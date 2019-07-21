SPEED_GRAMMAR = r"""
start: _speed_defs

_speed_defs: _speed_def
           | _speed_def "," _speed_defs

_speed_def: single_speed_def
          | single_speed_def "|" _speed_def

single_speed_def: _speed             -> normal_speed
                | "advisory:" _speed -> advisory_speed

_speed: speed_value _restriction_def
      | speed_value

_restriction_def: "(" _restrictions ")"

_restrictions: restriction
             | restriction "," _restrictions

restriction: weight                          -> weight_restriction
           | restriction_conditional         -> conditional_restriction
           | NUMBER+ "m"                     -> length_restriction
           | NUMBER+ "seats"                 -> seat_restriction
           | NUMBER+ "axles"                 -> axle_restriction

restriction_conditional: "articulated"  -> articulated
                       | "trailer"      -> trailer
                       | "caravan"      -> caravan
                       | "wet"          -> wet
                       | time_span      -> time

weight: WEIGHT "t"                   -> normal_weight
      | weight_qualifier WEIGHT "t"  -> qualified_weight_pre
      | WEIGHT "t" weight_qualifier  -> qualified_weight_post

weight_qualifier: "empty"     -> empty
                | "capacity"  -> capacity
                | "trailer"   -> trailer

_time_span: TIME "-" TIME
          | TIME "+" TIME
          
time_span: _time_span
         | "(" _time_span ")" "-" "(" _time_span ")"

speed_value: NUMBER+ "mph" -> mph_speed
           | NUMBER+       -> kph_speed
           | "walk"        -> walk_speed

WEIGHT: /\d+([.]\d+)?/

TIME: /[a-zA-Z0-9:]+/

%import common.INT -> NUMBER
%import common.WS
%ignore WS
"""