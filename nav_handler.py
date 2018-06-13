
NO_SYNC = 0
SUBFRAME_SYNC = 1
FRAME_SYNC = 2

TLM_WORD_DEF = [ # Word 1
            {
                'name': 'preamble',
                'msb':  1,
                'lsb':  8,
                'type': 'binary'
            }, {
                'name': 'tlm',
                'msb':  9,
                'lsb':  22,
                'type': 'binary'
            }
        ]

HOW_WORD_DEF = [ # Word 2
            {
                'name': 'tow_count',
                'msb':  1,
                'lsb':  17,
                'type': 'binary'
            }, {
                'name': 'alert_flag',
                'msb':  18,
                'lsb':  18,
                'type': 'boolean'
            }, {
                'name': 'antispoof_flag',
                'msb':  19,
                'lsb':  19,
                'type': 'boolean'
            }, {
                'name': 'subframe_id',
                'msb':  20,
                'lsb':  22,
                'type': 'int'
            }
        ]

# NAV message dictionary
# Frame
nav_dictionary = [
    [ # Subframe 1
        TLM_WORD_DEF,
        HOW_WORD_DEF,
        [ # Word 3
            {
                'name': 'week_num',
                'msb':  1,
                'lsb':  10,
                'type': 'int'
            }, {
                'name': 'l2_codes',
                'msb':  11,
                'lsb':  12,
                'type': 'binary'
            }, {
                'name': 'sv_accuracy',
                'msb':  13,
                'lsb':  16,
                'type': 'int'
            }, {
                'name': 'sv_health',
                'msb':  17,
                'lsb':  22,
                'type': 'int'
            }, {
                'name': 'iodc_msb',
                'msb':  23,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 4
            {
                'name': 'l2_nav_disabled',
                'msb':  1,
                'lsb':  1,
                'type': 'boolean'
            }
        ], [ # Word 5
        ], [ # Word 6
        ], [ # Word 7
            {
                'name': 't_gd',
                'msb':  17,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 8
            {
                'name': 'iodc_lsb',
                'msb':  1,
                'lsb':  8,
                'type': 'int'
            }, {
                'name': 't_oc',
                'msb':  9,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 9
            {
                'name': 'af2',
                'msb':  1,
                'lsb':  8,
                'type': 'int',
            }, {
                'name': 'af1',
                'msb':  9,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 10
            {
                'name': 'af0',
                'msb':  1,
                'lsb':  22,
                'type': 'int'
            }
        ]
    ], [ # Subframe 2
        TLM_WORD_DEF,
        HOW_WORD_DEF,
        [ # Word 3
            {
                'name': 'iode',
                'msb':  1,
                'lsb':  8,
                'type': 'int'
            }, {
                'name': 'c_rs',
                'msb':  9,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 4
            {
                'name': 'delta_n',
                'msb':  1,
                'lsb':  16,
                'type': 'binary'
            }, {
                'name': 'm0_msb',
                'msb':  17,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 5
            {
                'name': 'm0_lsb',
                'msb':  1,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 6 
            {
                'name': 'c_uc',
                'msb':  1,
                'lsb':  16,
                'type': 'int'
            }, {
                'name': 'e_msb',
                'msb':  17,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 7
            {
                'name': 'e_lsb',
                'msb':  1,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 8  
            {
                'name': 'c_us',
                'msb':  1,
                'lsb':  16,
                'type': 'int'
            }, {
                'name': 'sqrt_a_msb',
                'msb':  17,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 9
            {
                'name': 'sqrt_a_lsb',
                'msb':  1,
                'lsb':  24,
                'type': 'int'
            }
        ], [ # Word 10
            {
                'name': 't_oe',
                'msb':  1,
                'lsb':  16,
                'type': 'int'
            }, {
                'name': 'fit_interval',
                'msb':  17,
                'lsb':  17,
                'type': 'binary'
            }, {
                'name': 'aodo',
                'msb':  17,
                'lsb':  21,
                'type': 'binary'
            }
        ]
    ], [ # Subframe 3 
    ]
]

class NavHandler():

    words = []
    subframe = None
    word_index_in_subframe = None
    state = NO_SYNC

    def __init__(self):
        pass

    def reset(self):
        print('[nav_handler] reseting')

    def feed_word(self, word):

        self.words.append(word)

        print('\t[nav_handler] decoded word: {:024b}'.format(word))

        # Check for preamble
        if self.state == NO_SYNC:
            if (word  >> 16) & 0xff == 0b10001011:

                print('\t[nav_handler] subframe lock: TLM header detected')

                self.state = SUBFRAME_SYNC
                self.word_index_in_subframe = 1

        elif self.state == SUBFRAME_SYNC:
            self.word_index_in_subframe += 1
            if self.word_index_in_subframe == 2:
                tow =           (word >> 7) & 0x1ffff
                alert_flag =    (word >> 6) & 1
                antispoof_flag =(word >> 5) & 1
                subframe =      (word >> 2) & 0x7
                print('\t[nav_handler] SUBFRAME_SYNC: HOW: TOW: {}\tAlert: {}\tAntiSpoof: {}\tSubframe: {}'.format(tow, alert_flag, antispoof_flag, subframe))

                self.subframe = subframe
                self.state = FRAME_SYNC
        
        elif self.state == FRAME_SYNC:
        
            self.word_index_in_subframe += 1

            if self.word_index_in_subframe > 10:
                self.subframe += 1
                self.word_index_in_subframe = 1

                if self.subframe > 5:
                    self.subframe = 1

            word_definition = nav_dictionary[self.subframe-1][self.word_index_in_subframe-1]

            decoded = {}
            out = '\t[nav_handler] Subframe {} Word {}'.format(self.subframe, self.word_index_in_subframe)
            for field in word_definition:
                
                # okay we gotta convert dumb bit indices to real ones 
                # ICD bit 1 is actually bit 23
                # ICD bit 24 is actually bit 0
                width = field['lsb'] - field['msb'] + 1
                val = (word >> (24-field['lsb'])) & (2**width-1)
                
                if field['type'] == 'int' or field['type'] == 'boolean':
                    fmt_val = str(val)
                elif field['type'] == 'binary':
                    fmt_val = '{{:0{}b}}'.format(width).format(val) # :)

                out += ' {}: {}'.format(field['name'], fmt_val)
            print(out)

