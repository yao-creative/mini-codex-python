$$\text{Rust: } \quad \exists\, \text{compiler-checked } \varphi : \text{Ref} \to \mathbb{B}, \quad \varphi(r) \Leftrightarrow \ell_r \subseteq \ell_{\text{owner}(r)} \wedge |\{r' : r' \text{ mut-aliases } r\}| \le 1$$

$$\text{proved before execution; violation} \Rightarrow \text{program does not compile}$$

$$\text{Python: } \quad \nexists\, \varphi \quad \Rightarrow \quad \forall r,\ \ell_r \subseteq \ell_{\text{owner}(r)} \text{ and aliasing-safety are } \textbf{unchecked propositions}$$

$$\text{unchecked} \ne \text{false} — \text{just: no proof obligation discharged before runtime}$$

## What fills the gap — three substitute encodings, each converting the missing static proof into something else

$$\text{immutability: } \quad \forall r_1, r_2 \text{ aliasing } v: \ \text{mut}(v) = \varnothing \implies \text{(aliasing is now irrelevant, not prevented)}$$

$$\text{guard: } \quad \varphi \text{ moved from compile-time to a runtime predicate } g(v) : \text{call} \to \{\text{ok}, \bot\}, \text{ checked per-call, not per-compile}$$

$$\text{structural containment: } \quad \ell_{\text{child}} \subseteq \ell_{\text{scope}} \text{ enforced by control-flow blocking } (\text{TaskGroup.__aexit__ won't return until } \forall \text{child}: \text{end}_{\text{child}} \le t)$$

$$\text{net effect: } \quad \varphi_{\text{Rust}} \text{ is one static proof} \quad \longrightarrow \quad \varphi_{\text{Python}} = \varphi_{\text{immut}} \wedge \varphi_{\text{guard}} \wedge \varphi_{\text{scope}}, \text{ three independent, manually-discharged obligations, none load-bearing without the others}$$

Concretely: drop any one of the three for a given resource and $\varphi$ silently reverts to *unchecked* for exactly that resource — there's no fallback the language provides underneath.