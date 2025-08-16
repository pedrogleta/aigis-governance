import matplotlib.pyplot as plt
import numpy as np

# Generate data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
# Create plot
plt.figure(figsize=(10, 6))
plt.plot(x, y1, label="sin(x)", linewidth=2)
plt.plot(x, y2, label="cos(x)", linewidth=2)
plt.title("Trigonometric Functions")
plt.xlabel("x")
plt.ylabel("y")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
