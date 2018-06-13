PLL_KD = 1

def do_update(s_i, s_q, current_doppler, current_phase, end_t):

    new_doppler = current_doppler
    new_phase = current_phase

    # PLL (at least doppler tracking shit)
    # Trouble is, we need to do frequency shifts without changing phase. how do
    # AKA discriminator output / phase detector thingle
    inst_phase = math.atan2(result_q[2], result_i[2])

    error = (inst_phase - current_phase)
    #inst_phase = result_q[2] * result_i[2]
    inst_phase_deriv = angle_difference(inst_phase , last_inst_phase)
    # Don't change doppler if there's a huge ass phase change (NAV bit flip)
    # to prevent my shitty FLL fron unlocking :)
    if abs(inst_phase_deriv) < (0.6 * (math.pi)):
        new_doppler -= PLL_KD * inst_phase_deriv
    last_inst_phase = inst_phase

    # DOPPLER -> PHASE ADJUSTMENT
    # The value passed to cos() and sin() when generating carrier at end of this chunk.
    # Needs to stay the same when we shift freq (adjusting doppler)
    chunk_end_carrier_complete_phase = (2 * math.pi * f_carrier * end_t + phase)
    chunk_begin_carrier_complete_phase = (2 * math.pi * (front.F_L1_IF + doppler) * end_t + phase) 
    new_phase -= (chunk_begin_carrier_complete_phase - chunk_end_carrier_complete_phase)
    
    
