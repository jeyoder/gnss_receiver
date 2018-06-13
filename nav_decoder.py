import math
import nav_handler

class NavDecoder():


    SYM_THRESH = 0.25 * math.pi
    MEASUREMENTS_FOR_VALIDITY = 20

    handler = nav_handler.NavHandler()

    valid_measurements = 0
    bit_lock = False
    word_lock = False
    prev_word = None
    last_bit = None

    i = 0
    edge_detect = None

    bitstream = []

    def __init__(self, frontend):
        self.front = frontend

    # Parse word & check parity, returns a tuple of (decoded word, parity_ok (bool))
    def check_parity(self, w, prev_w):

        #prepend a zero so indexes match GPS-IS, dumb, yes 
        w.insert(0, 0)
        prev_w.insert(0, 0)

        if prev_w[30]:
            # invert data bits of w
            for i in range(1, 25):
                w[i] ^= 1

        pb1 = prev_w[29] ^ w[1] ^ w[2] ^ w[3] ^ w[5] ^ w[6] ^ w[10] ^ w[11] ^ w[12] ^ w[13] ^ w[14] ^ w[17] ^ w[18] ^ w[20] ^ w[23]
        pb2 = prev_w[30] ^ w[2] ^ w[3] ^ w[4] ^ w[6] ^ w[7] ^ w[11] ^ w[12] ^ w[13] ^ w[14] ^ w[15] ^ w[18] ^ w[19] ^ w[21] ^ w[24]
        pb3 = prev_w[29] ^ w[1] ^ w[3] ^ w[4] ^ w[5] ^ w[7] ^ w[8] ^ w[12] ^ w[13] ^ w[14] ^ w[15] ^ w[16] ^ w[19] ^ w[20] ^ w[22]
        pb4 = prev_w[30] ^ w[2] ^ w[4] ^ w[5] ^ w[6] ^ w[8] ^ w[9] ^ w[13] ^ w[14] ^ w[15] ^ w[16] ^ w[17] ^ w[20] ^ w[21] ^ w[23]
        pb5 = prev_w[30] ^ w[1] ^ w[3] ^ w[5] ^ w[6] ^ w[7] ^ w[9] ^ w[10] ^ w[14] ^ w[15] ^ w[16] ^ w[17] ^ w[18] ^ w[21] ^ w[22] ^ w[24]
        pb6 = prev_w[29] ^ w[3] ^ w[5] ^ w[6] ^ w[8] ^ w[9] ^ w[10] ^ w[11] ^ w[13] ^ w[15] ^ w[19] ^ w[22] ^ w[23] ^ w[24]

        ok = (w[25] == pb1 and w[26] == pb2 and w[27] == pb3 and w[28] == pb4 and w[29] == pb5 and w[30] == pb6)

        # Pack word into bits
        word = 0
        for i in range(24):
            word |= (w[24-i] << i)

        return (word, ok)

    def feed_measurement(self, z_i, z_q):
        

        # Integrity checking: instantaneous phase angle should be
        # zeroish or pi-ish
        inst_phase = math.atan2(z_q, z_i) if z_i != 0 else 0

        bit = 1 if z_i > 0 else 0

        # CRAPPY CRAP TODO: actual PLL lock detection
        if(z_i > 0):
            bit_valid = (abs(inst_phase) < self.SYM_THRESH)
        else: # inst_phase on pi/2->pi, -pi->-pi/2
            bit_valid = abs(inst_phase) > (math.pi - self.SYM_THRESH)

        if bit_valid:
            self.valid_measurements += 1
        else:
            self.valid_measurements -= 5

        if self.valid_measurements >= 30:
            self.valid_measurements = 30
        elif self.valid_measurements < 0:
            self.valid_measurements = 0
        
        bit_lock = (self.valid_measurements > self.MEASUREMENTS_FOR_VALIDITY)
        
        if bit_lock and self.bit_lock != bit_lock:
            print('[nav_decoder] Got bit lock')
        elif not bit_lock and self.bit_lock != bit_lock:
            print('[nav_decoder] Lost bit lock')
        # END CRAPPY CRAP


        # Do things with bit
        if (self.bit_lock and bit != self.last_bit):
            if self.edge_detect is None:
                print('[nav_decoder] Syncing to first edge_detect at i={}'.format(self.i))
            self.edge_detect = self.i 

        # Sample 10 ms into NAV bit, i.e. (20 * n) + 10 ms from i
        if self.bit_lock and self.edge_detect is not None and (self.i - self.edge_detect) % 20 == 10:
           # print('[nav_decoder] Sampling NAV bit: {}'.format(bit))
            self.bitstream.append(bit)

            # If we have enough bits in the bitstream to reliably check parity, do so
            WORD_LEN = 30
            NUM_WORDS_TO_CHECK = 2

            if self.word_lock:
                # Decode words??? our bitstream log should be aligned to word boundaries now, so thats cool
                if len(self.bitstream) == WORD_LEN:
                    (word, parity_ok) = self.check_parity(list(self.bitstream), list(self.prev_word))
                    if(parity_ok):
                        self.handler.feed_word(word)
                        self.prev_word = list(self.bitstream)
                        self.bitstream = []
                    else:
                        print('[nav decoder] lost word lock')
                        print('[nav decoder] forbidden word was: {}'.format(self.bitstream))
                        self.word_lock = False
                        self.handler.reset()

            elif len(self.bitstream) == WORD_LEN * (NUM_WORDS_TO_CHECK+1): # if we have X words' worth of bits in the buffer
                print('[nav_decoder] Attempting word lock @ {}'.format(self.i))
                word_match = True
                for word_num in range(NUM_WORDS_TO_CHECK):
                    prev_word = self.bitstream[(word_num+0) * WORD_LEN:(word_num+1) * WORD_LEN]
                    word = self.bitstream[(word_num+1) * WORD_LEN:(word_num+2) * WORD_LEN]

                    decoded_word, parity_ok = self.check_parity(list(word), list(prev_word))
                    word_match &= parity_ok

                    # check the parity of word...
#                    print('[nav_decoder] word: ' + str(word) + '?: {}'.format(parity_ok))

                if word_match:
                    print('[nav_decoder] Got word lock also word is {}'.format(len(word)))
                    self.prev_word = word
                    self.bitstream = [] 
                    self.word_lock = True
                    self.handler.feed_word(decoded_word)
                else:
                    del self.bitstream[0] 

        self.bit_lock = bit_lock 
        self.last_bit = bit
        self.i += 1
