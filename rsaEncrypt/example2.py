from Cryptodome.PublicKey import RSA


def create_rsa_key():
    '''生成RSA秘钥对'''
    try:
        # 选择秘钥位数，位数越高越安全，同时加密速度也越慢
        key = RSA.generate(2048)
        encrypted_key = key.exportKey(pkcs=8)

        public_key = key.publickey().exportKey().decode('utf-8')
        private_key = encrypted_key.decode('utf-8')

        return {'state': 1, 'message': {'public_key': public_key, 'private_key': private_key}}
    except Exception as err:
        return {'state': 0, 'message': str(err)}

if __name__ == '__main__':
    print(create_rsa_key())

import binascii
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5


class RsaCrypto():
    '''RSA 加解密'''

    def __init__(self):
        self.private_key = '''-----BEGIN PRIVATE KEY-----
        MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDLetN9MfsVWZj2
        K+i1vPQqeDKb8Fe52pHKvRtQggTF+x3YRCyk7UNQ27VupohM8t+Qzi2Zm3GnZY5X
        H7W8UGLnI1X1ykpWOWVueP3KCA7DCtswDp5hkJgHzPPZC/DlFh0uCpAmUkgHP7WU
        XRZoR9mmcVOdWN9c+NWS0JA6cwHSI+J78Edb1lfef5YOwseL2GiOmBiJ7THYfjrw
        FwGQaZVjhsp3Pkt7Yt/Huc5NU234wA9j+TFFnubpOrE9mFT8qCkhFhWIEcNsuTqD
        DDI9BX0lLaEEn+vg9cnEZ97VgdQQG2D6Ozw4Gldpfoq1XB6BqXg+YsCvyD/h/4QD
        LpejZy/VAgMBAAECggEADJkoj6omNevb459Tri+VHS1fUiEEXXZ3QQqKWWa4wu/0
        U2030mek8P8EHGYP2avOmcRE4IDWUvCfv9cvxQljxj8oKwABBZZSKGUyBBiRnr6E
        /v8OC/5hhgIeNZm0ADW+osN2qgNoKu1lNwVjG3EaEbXB4TkdGJWI1lPhdNelYjby
        7/4vnXO7yplSFlDLiqjmEV9Vva3Jf3N3vf92ZfUJg6NHklYDlP+L4unNtS++HKtv
        C3TWSz0esVrK67t4Vut+RdKrSQzzWkPAqNwktUavQq6Nb+KMrf9tsQujPZaXkEUn
        LUwtVNwhT3BiyPswHN1ycjlP3lN391rnawDQc751dQKBgQDZSFBq1JaGm4zK2YHm
        BbxCJ++6l1Qmu9yhk/zic1M/oGoFRdzkeWrYsxhLupp+4PjcCPEiZqivSeJXsFVO
        diSjWsBkfO51HRuEzRE2Z/tiTRzJsGAcrBsWwBYNZR/PADG7MEYhIYH0p6Jp3jrq
        pNs0f5Gz8XToPi2TQXmRyAltFwKBgQDvvOFlJFfx1ld2wLuZ0w1yMpUoyFYCWSh+
        ylREFETod8ufbQxRzvvSA3gFO+xwYZoA+Wq/TyGrfVnN9m4R1goPsQjsuUYQeAIi
        MBKmG5znTAmu8dQ5wLKtb10CV0MuFGOSv8xvlccKepY7IDtxOaO410o4PFEjAziU
        90b8RiRV8wKBgHDsUD71NTXH6agS2pu9J1YKg2Cp/SYURFoFG0xlO0K6D9+lq2Ni
        ZtEwYtQYqup96VgRnaCPUeOntmZ0UiFw7SGorIyNETD0a7TdDrED4XX5NZjsfUbp
        ezqbodpcT+e45h+uuwPE8lFAPfxfbqc7/mCOXB70whlhFzaMtK27FIsJAoGAVtTJ
        qnF8bPpeWYO7Lx7TOu55Ofk9tcIHOc0csj/JKY3iMY80rBjU+p8JBJRMsfOX7Qxp
        jnshzdQsB75e5ZTptf9AJUWBzAs7cpiI2KMdtGTFCRlL7dMOpGS2gleK3JDD8+4G
        JNBR9EisSyQEg6EF3LgViMLH/G95OfNKQatCE+MCgYEAhRIuEMaL2idD9NKOVdgC
        fuSbiP5G69IBVD4uoDYFPQJjxqVOg3pORa8+cJTe+ZFaCkTGV3112eM5Vtm4Vd9Q
        pOh7VgJP1l3puZnUoSWGoWansx6aKok5FwuUrZWPjqr/Zrre8XXJyaiR520tuf0i
        StMfNAsijJgi2pq2PTMovhE=
        -----END PRIVATE KEY-----'''

        self.public_key = '''-----BEGIN PUBLIC KEY-----
        MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy3rTfTH7FVmY9ivotbz0
        Kngym/BXudqRyr0bUIIExfsd2EQspO1DUNu1bqaITPLfkM4tmZtxp2WOVx+1vFBi
        5yNV9cpKVjllbnj9yggOwwrbMA6eYZCYB8zz2Qvw5RYdLgqQJlJIBz+1lF0WaEfZ
        pnFTnVjfXPjVktCQOnMB0iPie/BHW9ZX3n+WDsLHi9hojpgYie0x2H468BcBkGmV
        Y4bKdz5Le2Lfx7nOTVNt+MAPY/kxRZ7m6TqxPZhU/KgpIRYViBHDbLk6gwwyPQV9
        JS2hBJ/r4PXJxGfe1YHUEBtg+js8OBpXaX6KtVwegal4PmLAr8g/4f+EAy6Xo2cv
        1QIDAQAB
        -----END PUBLIC KEY-----'''

    def encrypt(self, plaintext):
        '''加密方法'''
        try:
            recipient_key = RSA.import_key(self.public_key)
            cipher_rsa = PKCS1_v1_5.new(recipient_key)

            en_data = cipher_rsa.encrypt(plaintext.encode('utf-8'))
            hex_data = binascii.hexlify(en_data).decode('utf-8')

            return {'state': 1, 'message': hex_data}
        except Exception as err:
            return {'state': 0, 'message': str(err)}

    def decrypt(self, hex_data):
        '''解密方法'''
        try:
            private_key = RSA.import_key(self.private_key)
            cipher_rsa = PKCS1_v1_5.new(private_key)

            en_data = binascii.unhexlify(hex_data.encode('utf-8'))
            data = cipher_rsa.decrypt(en_data, None).decode('utf-8')

            return {'state': 1, 'message': data}
        except Exception as err:
            return {'state': 0, 'message': str(err)}


if __name__ == '__main__':
    print(RsaCrypto().encrypt())