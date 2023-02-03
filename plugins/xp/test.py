"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import matplotlib.pyplot as plt
import numpy as np
import math

t, dt = np.linspace(0, 12, 1000, endpoint=True, retstep=True) # time in months

def lose(xp, N, t):
    if t < 1:
        return 0
    return xp * N**(t-1) * np.log(N)  # derivative of xp * (1/N)**(-t)

XP = 1000
N = 0.3

xp = np.empty_like(t)
xp[0] = XP

for i in range(len(t)-1):
    xp[i+1] = xp[i] + lose(xp[i], N, t[i]) * dt

plt.plot(t, xp)
plt.grid()
plt.show()
