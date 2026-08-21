
# Code Built Well and Algebraically

Everything is Functional down to resource.

## Dataclasses:
1. All inheritances must be a complete chain of subsets eg: Event -> <StateClass>Event -> <StateClass>Event<Type>. Without a jump from 1 to 3 so that events are restricted to their state class and impossible transitions on orthogonal stateclasses are irrepresentable.
2. 


## States
1. Type definitions of Mutable containers. 
2. All states rest on a DAG/ Poset from Config -> AppState. Incomparable states are orthogonal.
3. They are containers they don't own their own morphisms
4. Each state has a manager which owns all of the morphisms of the runtime instance and the eval of morphisms on them

## Events 
1. Immutable data types.
2. Trigger a transition to the corresponding State class via the application function of State x Event -> State'


