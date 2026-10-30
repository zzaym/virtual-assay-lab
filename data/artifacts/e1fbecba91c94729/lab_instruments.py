"""Real PyLabRobot 0.2.2 frontends with HTTP simulation backends.

This models a preloaded single-channel reagent dispenser; tip geometry and motion
are illustrative. Reagent consumption and assay state are authoritative on the server.
"""
from pylabrobot.resources import Plate, Well, Deck, Coordinate, Tip, create_ordered_items_2d
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends.chatterbox import LiquidHandlerChatterboxBackend
from pylabrobot.plate_reading import PlateReader
from pylabrobot.plate_reading.chatterbox import PlateReaderChatterboxBackend


def assay_plate(name):
    return Plate(name,127.76,85.48,14.4,ordered_items=create_ordered_items_2d(
        Well,48,32,dx=9,dy=5,dz=1,item_dx=2.25,item_dy=2.25,
        size_x=1.6,size_y=1.6,size_z=10,max_volume=12))


class ReagentBackend(LiquidHandlerChatterboxBackend):
    def __init__(self,client,plate_id):
        super().__init__(num_channels=1);self.client=client;self.plate_id=plate_id
    async def setup(self):pass
    async def stop(self):pass
    async def dispense(self,ops,use_channels,**kwargs):
        for op in ops:
            self.client.step("add_ctg",plate_id=self.plate_id,wells=[op.resource.parent.get_child_identifier(op.resource)],
                             volume_uL=op.volume,driver="PyLabRobot 0.2.2 LiquidHandler.dispense")


class LuminescenceBackend(PlateReaderChatterboxBackend):
    def __init__(self,client,plate_id):
        super().__init__();self.client=client;self.plate_id=plate_id
    async def setup(self):pass
    async def stop(self):pass
    async def read_luminescence(self,plate,wells,focal_height):
        if focal_height!=10:raise ValueError("The virtual reader is calibrated at focal_height=10 mm.")
        result=self.client.step("read",plate_id=self.plate_id,driver="PyLabRobot 0.2.2 PlateReader.read_luminescence")
        data=[[None for _ in range(48)] for _ in range(32)]
        for w in wells:
            key=plate.get_child_identifier(w)
            if key in result["wells"]:data[plate.get_child_row(w)][plate.get_child_column(w)]=result["wells"][key]
        return [{"time":result["simulated_hours"]*3600,"temperature":22.,"data":data}]


async def detect_and_read(client,plate_id):
    """Example SOP, executed through real PLR methods; returns raw reader matrix."""
    observation=client.observe();names=list(observation["plates"][plate_id]["wells"])
    plate=assay_plate(plate_id);deck=Deck(300,200,100);deck.assign_child_resource(plate,Coordinate(0,0,0))
    lh=LiquidHandler(ReagentBackend(client,plate_id),deck);await lh.setup()
    tip=Tip(False,50,300,5);tip.tracker.set_volume(300)
    lh.head[0].add_tip(tip,commit=True)
    for name in names:await lh.dispense([plate.get_well(name)],vols=[2.5],use_channels=[0])
    await lh.stop()
    client.step("wait_detection",plate_id=plate_id,minutes=10)
    deck.unassign_child_resource(plate)
    reader=PlateReader("CTG_reader",150,150,200,LuminescenceBackend(client,plate_id))
    reader.assign_child_resource(plate);await reader.setup()
    result=await reader.read_luminescence(focal_height=10,wells=[plate.get_well(n) for n in names],use_new_return_type=True)
    await reader.stop()
    return result
