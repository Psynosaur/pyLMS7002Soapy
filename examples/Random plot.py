import numpy as np
import pylab as plt
import matplotlib.ticker as ticker

# Generate data
x = np.linspace(0, 1e-9)
y = 1e3 * np.sin(2 * np.pi * x / 1e-9)  # one period, 1k amplitude

# setup figures
fig = plt.figure()
ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)
# plot two identical plots
ax1.plot(x, y)
ax2.plot(x, y)

# Change only ax2
scale_x = 1e-9
scale_y = 1e3
ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x / scale_x))
ax2.xaxis.set_major_formatter(ticks_x)

ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x / scale_y))
ax2.yaxis.set_major_formatter(ticks_y)

ax1.set_xlabel("meters")
ax1.set_ylabel('volt')
ax2.set_xlabel("nanometers")
ax2.set_ylabel('kilovolt')

plt.show()
