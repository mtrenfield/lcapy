from lcapy import Opamp, R, Series

# Create simple non-inverting amplifier
Rf = 1000
R1 = 50

a = Opamp()

# Add feedback resistor.
b = a.bridge(R(Rf), 2, 3)

# Connect R1 to ground.
c = b.terminate(R(R1))

print c.Vtransfer

