import mido 

controls = {
    'BOOSTER': 16,
    'MOD': 17,
    'DELAY': 18,
    'REVERB': 19,
    'GAIN': 20,
    'MASTER': 21
}

with mido.open_output('2- KATANA 1') as port:
    for name, cc in controls.items():
        msg = mido.Message('control_change', control=cc, value=100)
        port.send(msg)
        print(f"Sent {name} control (CC#{cc}) = 100")