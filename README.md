
# Code Built Well and Algebraically

## States
1. Type definitions of Mutable containers. 
2. All states rest on a DAG/ Poset from Config -> AppState. Incomparable states are orthogonal.
3. They are containers they don't own their own morphisms
4. Each state has a manager which owns all of the morphisms of the runtime instance and the eval of morphisms on them


