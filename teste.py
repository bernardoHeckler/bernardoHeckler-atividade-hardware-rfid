from mfrc522 import SimpleMFRC522

leitorRfid = SimpleMFRC522()

tag = leitorRfid.read()
print('tag', tag)
