# Example 'Code Run' (1093972916)

## Run inline code `print(6 * 6)`{=python} (90e43264-471a-4da9-b340-0b519f80f1b9)

Answer with `print('inline')`{=python} code

## Question with code block that resolves to output text: (fc59dd82-0535-4e5a-8927-3b2dbab902b7)

```{=cpp}
#include <iostream>
using namespace std;

int main() {
	cout << "Hello World! (c++)" << endl; // prints Hello World!
	return 0;
}
```

```{=typescript}
let message: string = 'Hello, World! (typescript)';
console.log(message);
```

---

Answer with code block:

```{=cpp}
#include <iostream>
using namespace std;

int main() {
	cout << "Bye World!" << endl; // prints Hello World!
	return 0;
}
```

## Question with matplotlib graph (d49a8734-1ab7-4b18-a717-c68d6304658d)

```{=jupyter_notebook_matplotlib}
import numpy as np
import matplotlib.pyplot as plt

def m_t_exp_wachstum(c, k, t):
    return c * np.exp(k * t)

def m_t_exp_wachstum_abl(c, k, t):
    return k * m_t_exp_wachstum(c, k, t)

x = np.linspace(0, 200)
y_m_t = m_t_exp_wachstum(c=30, k=-0.04, t=x)
y_m_t_abl = m_t_exp_wachstum_abl(c=30, k=-0.04, t=x)

plt.plot(x, y_m_t, "-b", label="$M_{vereinfacht}(t)$")
plt.xlabel("$t$ (in min)")
plt.legend(loc="upper right")
plt.savefig("graph_1.svg")

plt.plot(x, y_m_t_abl, "-r", label="$M_{vereinfacht}'(t)$")
plt.xlabel("$t$ (in min)")
plt.legend(loc="upper left")
plt.savefig("graph_2.svg")
```

---

Answer

```{=jupyter_notebook_matplotlib}
import numpy as np
import matplotlib.pyplot as plt

def m_t_exp_wachstum(c, k, t):
    return c * np.exp(k * t)

def m_t_exp_wachstum_abl(c, k, t):
    return k * m_t_exp_wachstum(c, k, t)

x = np.linspace(0, 200)
y_m_t = m_t_exp_wachstum(c=30, k=-0.04, t=x)
y_m_t_abl = m_t_exp_wachstum_abl(c=30, k=-0.04, t=x)

plt.plot(x, y_m_t, "-b", label="$M_{vereinfacht}(t)$")
plt.xlabel("$t$ (in min)")
plt.legend(loc="upper right")
plt.savefig("graph_3.svg")
```
