import math

# lol params
KP = 50
KI = 1

first_integrator_output = 0

def do_update(s_i, s_q, current_doppler, current_phase):
    global first_integrator_output

    # Costas loop error function (easy mode / 180-degree shift insensitive)
    L_theta = -(s_i * s_q)
    #L_theta = math.atan2(s_i , s_q)

    first_integrator_output += KI * L_theta
    current_phase += first_integrator_output + KP * L_theta

    return current_phase
