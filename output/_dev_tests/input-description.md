### LIST OF VARIABLES IN input.json. EXAMPLE OF input.json FILE IS IN THIS FOLDER.

##### "XML_file"
String, name of the TTI file in which messages should be ranked, placed next to input.json file.  
Can be given with or without ".xml".
##### "ccp"
String, "lat, lon" of current car position.
##### "destination"
String, "lat, lon" of destination position, can be skipped if script run in "around" mode.  
##### "inner_radius"
Integer, radius of inner circle.
##### "outer_radius"
Integer, radius of outer circle.
##### "3rd_radius"
Integer, radius of 3rd circle. Can be set "endless" by putting -1, then all messages outside outer radius will be 
treated as in 3rd radius.
##### "ccp_dest_buffer_[km]"
Integer, width of the buffer around ccp->destination line (let's say radius, not diameter of buffer), when message is 
located farther from the line than buffer's value, it will receive negative ccp->destination line score (of course the 
farther, the move negative the score), according to formula:   
`1 - (distance / buffer)`  
Can be skipped if script run in "around" mode.  
<br><br>
##### "limit"
Integer, to what number final set of messages should be limited.
##### "ranking_score_capping"
Float, every message that has final (so-called "ranking") score below the capping value, will be removed from final set 
of messages.  
Ranking score can be a negative value, it depends on distance score and ccp->destination line score and their weights 
relatively to other scores and values they generated.  
But negative ranking score does not mean message will be automatically disregarded.  
By capping messages below certain level (e.g. -0.5) can be disregarded.
##### "bearing_filter_range"
Integer, ideally between 0 and 180. Amount of degrees on both left and right side of ccp->dest line in which messages 
are unfiltered outside inner radius.  
0 will remove all messages outside inner radius.  
45 will create a 90 degree cone around ccp->dest line (45 degrees on both sides of the line).  
180 will turn off the filter.  
Works in "bearing" and "line" modes.
##### "filtering_function"
Object of String keys and values. Keys are "inn_r_exclude", "out_r_exclude", "3rd_r_frcs_include", 
"3rd_r_events_include", "excluded_completely".  
Values are Strings, but can be list like "FRC0,FRC1,FRC2", they will be parsed and treated as list.  
They are responsible for: "inn_r_exclude" on which FRCs to exclude messages in inner radius, and so on. 
"excluded_completely" will remove every message of certain type.
<br><br>
##### "distance_score"
"calculated on ccp, incident position and outer radius" is just a comment.
##### "radius_boost_score"
Object of String keys and Float values.  
In first key: radius in which messages get certain score can be specified (provided in value connected to key).  
Other 2 keys are "inn_r" (value for messages between radius from first key and inner radius) and "else" (score outside 
inner radius).
##### "event_score"
Object of String keys and Float values, keys are different message types (e.g. "JAM_UNCONDITIONAL", "CLOSURE"), in 
values there are scores associated with it.
##### "jam_priority"
**DOES NOT WORK FOR NOW**  
Object of String keys and Float values. Different jam priorities (e.g. "101", "108") and values associated with them.
##### "frc_score"
Object of String keys and Float values. Different FRCs (e.g. "FRC1", "FRC2") and values associated with them.
##### "delay_score"
Object of String keys and Float values. Different delay thresholds in seconds (e.g. "300", "420") and values for 
message that has delay lower or equal to threshold.
##### "excluded_from_delay_score"
List of Strings, list of message types that are excluded from delay score, they will automatically receive score **1**! 
Designed mainly for "CLOSURES" which do not have delay, but are affecting the routing, so should receive the highest 
score.  
If message type is not specified on this list, but does not have delay: it will receive delay score **0** (the lowest 
value).
<br><br>
##### "weights"
Object of String keys and Float values. Weights for final, ranking score. Keys are "distance_score", "event_score", 
"frc_score",  "delay_score", "radius_boost_score", "ccp_dest_line_score".  
Formula for the score if the message was not prefiltered or some attribute/score could not be obtained/calculated 
(due to unexpected error):  
`distance_score * it's weight + event_score * it's weight + frc_score * it's weight + so on...`  
Giving a weight value **0** will turn off the score, but it's "chunk of weight" should be distributed to other score(s).  
Values are floats and ideally **should add up to 1**.  
Remember, when calculating score in "around" or "bearing" mode do not leave any weight for "ccp_dest_line_score"
as it does not work in those cases, and it will lower all message scores.  
The bigger the country TTI file comes from, more negative values of the ranking score, it depends on weight of 
distance score and ccp->destination line score. Impact of both can be affected by, of course, scores weights, but 
also ccp_dest_buffer_[km] attribute described above.
