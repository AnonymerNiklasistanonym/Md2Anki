# Example 'Code Run' (1093972916)

## Run inline code `print(6 * 6)`{=py} (90e43264-471a-4da9-b340-0b519f80f1b9)

Answer with `print('inline')`{=py} code

## Question with code block that resolves to output text: (fc59dd82-0535-4e5a-8927-3b2dbab902b7)

```{=cpp}
#include <iostream>
using namespace std;

int main() {
	cout << "Hello World! (c++)" << endl; // prints Hello World!
	return 0;
}
```

```{=ts}
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

```{=py}
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

```{=py}
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

```{=latex}
\documentclass[tikz,border=10pt]{standalone}
\usetikzlibrary{positioning}
\tikzset{
    main
    node/.style={circle,fill=none,draw,minimum size=1cm,inner sep=0pt}
}
\begin{document}
\begin{tikzpicture}
    \node[main node] [                                 ] (1)  {$1$};

    \node[main node] [below left  = 1cm and 1.5cm  of 1] (2)  {$2$};
    \node[main node] [below right = 1cm and 1.5cm  of 1] (3)  {$8$};

    \node[main node] [below left  = 1cm and 0.5cm  of 2] (4)  {$3$};
    \node[main node] [below right = 1cm and 0.5cm  of 2] (5)  {$7$};

    \node[main node] [below left  = 1cm and 0.5cm  of 3] (6)  {$9$};
    \node[main node] [below right = 1cm and 0.5cm  of 3] (7)  {$10$};

    \node[main node] [below left  = 1cm and 0.5cm  of 4] (8)  {$4$};
    \node[main node] [below right = 1cm and 0.5cm  of 4] (9)  {$5$};

    \node[main node] [below left  = 1cm and 0.5cm  of 7] (10) {$11$};
    \node[main node] [below right = 1cm and 0.5cm  of 7] (11) {$12$};

    \node[main node] [below left  = 1cm and 0.5cm  of 9] (12) {$6$};

    \path[draw,thick]
    (1) edge node {} (2)
    (1) edge node {} (3)

    (2) edge node {} (4)
    (2) edge node {} (5)

    (3) edge node {} (6)
    (3) edge node {} (7)

    (4) edge node {} (8)
    (4) edge node {} (9)

    (7) edge node {} (10)
    (7) edge node {} (11)

    (9) edge node {} (12)
    ;
\end{tikzpicture}
\end{document}
```
