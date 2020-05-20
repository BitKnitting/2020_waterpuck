# The front yard has one valve.
# it is on the wemos GPIO 4, which is I believe D2.
from waterpuck import WaterPuck
water_puck = WaterPuck(4)
water_puck.listen(8006)
