s --> np, vp.
np --> det, n.
np --> det, n, pp.
np --> pron.
vp --> v.
vp --> v, np.
vp --> v, np, pp.
pp --> p, np.

pron --> ["I"].
det --> ["the"].
det --> ["an"].
det --> ["my"].
n --> ["elephant"].
n --> ["pajamas"].
v --> ["sneezed"].
v --> ["shot"].
p --> ["in"].

parse(String) :-
    split_string(String, ' ', '', List),
    writeln(List),
    s(List, []).

:- visible(+all), leash(-all), trace, parse("I shot an elephant in my pajamas"), notrace.
