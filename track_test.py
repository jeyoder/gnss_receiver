#!/usr/bin/python3

import math
import numpy
import scipy
import matplotlib.pyplot as plt

import acquire
import frontend
import codegen_gpsl1ca
import nav_decoder

import pll

TAP_SPACING = 0.5
CHIP_RATE=1023000
CODE_LENGTH=1023

prn = 1 

# Get a chunk of data to acquire
front = frontend.Bavaro('bavaro.bin')
nav_decoder = nav_decoder.NavDecoder(front)

result = acquire.acquire(prn, front)
#result = {
#    'doppler' : -2000,
#    'delay' : 983
#}
print('\n')
print(result)
print('\n')

# Initialize tracking loop process variables
doppler = result['doppler'] 
delay   = result['delay']
phase   = 0 #wat do

last_inst_phase = 0

original_delay = delay

# I hope this is right :)
def angle_difference(a, b):
    a = a % (math.pi*2)
    b = b % (math.pi*2)

    result = None

    if (a - b > (math.pi)):
        result = ((a - math.pi*2) - b) % (math.pi*2)
    elif (a - b < (-math.pi)):
        result =  (a - (b-math.pi*2)) % (math.pi*2)
    else:
        result =  a - b

    if(result > math.pi):
        result -= 2*math.pi
    
    return result

#delay = 984

DLL_KP = 0.1

total_sample_count = 0

dll_steers = []
delayz = []
peaks = []

phase_ests = []
phase_derivs = []
dopplers = []

i_s = []
q_s = []

data_bits = []

front.skip(2000)

for i in range(60000):

    if i % 100 == 0:
        print('Iter: {} Delay: {}'.format(i, delay))

    buff = front.get_chunk(front.SAMPLES_PER_CHUNK)

    t = numpy.zeros(front.SAMPLES_PER_CHUNK)
    for samp_num in range(front.SAMPLES_PER_CHUNK):
        t[samp_num] = (i * front.SAMPLES_PER_CHUNK + samp_num) / front.F_SAMP

    code_bits = codegen_gpsl1ca.CODE[prn] # need to upsample

    delayed_codes = []

    i = numpy.arange(front.SAMPLES_PER_CHUNK)
    chip_num = (i * CHIP_RATE / front.F_SAMP).astype(numpy.uint32) % CODE_LENGTH # floor, not round, to simulate FIRness
    code = code_bits[chip_num] * 2 - 2

    # Generate carrier...
    f_carrier = front.F_L1_IF + doppler
    carrier_i = (numpy.sign(numpy.cos(2 * math.pi * f_carrier * t + phase))).astype('int32')
    carrier_q = (numpy.sign(numpy.sin(2 * math.pi * f_carrier * t + phase))).astype('int32')

    # Mix with carrier
    carrier_mixed_i = carrier_i * buff
    carrier_mixed_q = carrier_q * buff

    result_i = []
    result_q = []
    result_p = []

    # Perform 3 correlations (early/prompt/late), then a yolo to compare against
    #delays = numpy.arange(0, 1023, 0.1)
    delays = [0, delay-TAP_SPACING/2, delay, delay+TAP_SPACING/2]
    for chip_delay in delays:

        sample_delay = int(round(chip_delay * (front.F_SAMP / CHIP_RATE)))
        delayed_code = numpy.roll(code, sample_delay) #NOTE: assumes the chunk length is a multiple of the code length, otherwise we can't just circularly roll a superchunk

        # Convolutinate (I&Q)
        sum_i = float(numpy.correlate(carrier_mixed_i, delayed_code))
        sum_q = float(numpy.correlate(carrier_mixed_q, delayed_code))

        # Normalize sums... divide by the number of samples in the chunk
        sum_i /= delayed_code.shape[0] 
        sum_q /= delayed_code.shape[0] 

        result_i.append(sum_i)
        result_q.append(sum_q)
        
        result_p.append(math.sqrt(sum_i**2 + sum_q**2))

    # PLL tracking from prompt tap results
    s_i = result_i[2]
    s_q = result_q[2]

    nav_decoder.feed_measurement(s_i, s_q)

    phase = pll.do_update(s_i, s_q, doppler, phase)

    result_yolo = result_p[0]
    result_early = result_p[1]
    result_prompt = result_p[2]
    result_late = result_p[3]

    dll_steer_input = result_late - result_early
    delay += dll_steer_input * DLL_KP

    dll_steers.append(dll_steer_input)
    peaks.append(result_prompt)
    delayz.append(delay - original_delay)

    phase_ests.append(phase)
    phase_derivs.append(s_i * s_q)
    dopplers.append(doppler/1000)

    i_s.append(s_i)
    q_s.append(s_q)

plt.plot(dll_steers, label='DLL Steer Input')
plt.plot(peaks, label='Prompt Tap')
plt.plot(delayz, label='Code Delay Offset')
plt.legend()
plt.title('DLL Performance')
plt.show()

plt.plot(phase_ests, 'ro-', label='Theta_hat (radians)')
plt.plot(phase_derivs, 'bo-', label='L_theta')
plt.plot(dopplers, 'go-', label='Doppler/1000')
plt.legend()
plt.title('PLL Performance')
plt.show()

plt.plot(i_s[4000:], q_s[4000:], 'ro', label='IQ plot')
plt.title('IQ plot')
plt.show()

plt.plot(i_s, 'ro-')
plt.title('I channel (data bits)')
plt.show()

    #print('YOLO \t({}): \t\tI:{:.3f} Q:{:.3f}'.format(delays[0], result_i[0], result_q[0]))
    #print('EARLY \t({}): \t\tI:{:.3f} Q:{:.3f}'.format(delays[1], result_i[1], result_q[1]))
    #print('PROMPT \t({}): \t\tI:{:.3f} Q:{:.3f}'.format(delays[2], result_i[2], result_q[2]))
    #print('LATE \t({}): \t\tI:{:.3f} Q:{:.3f}'.format(delays[3], result_i[3], result_q[3]))


print(result)
