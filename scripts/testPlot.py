import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Generate some sample data
x = np.logspace(1, 3, num=100)  # Example data from 10^1 to 10^3
y = np.random.randn(100)

# Create the plot
plt.plot(x, y)

# Set the x-axis to use a logarithmic scale
plt.xscale("log")

# Define the desired number of ticks
num_ticks = 6

# Calculate the tick positions
tick_positions = np.logspace(1, 3, num=num_ticks, endpoint=True, base=10.0)

# Create a FixedLocator with the calculated tick positions
plt.gca().xaxis.set_major_locator(ticker.FixedLocator(tick_positions))

# Format the tick labels as desired
plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: "{:.0f}".format(x)))

# Show the plot
plt.show()
