from waterpuck import WaterPuck
# Back yard ---> Green = wemos D1 = GPIO 5, Blue = wemos D5 = GPIO 14
water_puck = WaterPuck(12, 14, 27)
water_puck.listen(8007)
