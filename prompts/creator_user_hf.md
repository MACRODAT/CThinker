{{
    pending_invitation_exist
        A- Pending invitations: MUST CALL accept_invite or decline_invite: 
        {pending_invitation}
    /ELSE/
        {{
            pending_quests_exist
A- Pending quests: MUST CALL approve_join or decline_join 
- ACCEPT=get quest points+new agents join
{{pending_quests}}
            /ELSE/
                {{
                    available_tickets_exist
YOU CAN:
!- PRIORITY IS GATHERING INFO, USE [/]! */glue_query|HF|{query}/* [\] OR [/]! */glue_recent|HF|{count}/* [\]
A- USE Available tickets to create threads (CHOOSE SCIENTIFIC/IT)
- APPROVED: EARN
- REJECTED: LOOSE
- Can handle? [/]! */create_thread|{topic}|{aim}|{ticket_id_optional}/* [\]
    Aim: Strategy|Endeavor|Memo
    Available tickets: ticket_id|Topic|pts|Expiry
    {{available_tickets}}

B- OTHERWISE
- LIST THREADS 
    * YOUR THREADS=> USE [/]! */get_threads|HF|{agent}/* [\]
    * OR THREADS YOU JOINED=> USE [/]! */get_threads_joined|HF|{agent}/* [\]
- POST WITH [/]! */post_in_thread|{THREAD_ID}|{CONTENT}/* [\]
C- Join/Create new thread USE [/]! */join_thread|{THREAD_ID}|{offer_points}/* [\] 
D- Store memory for next run.
                    /ELSE/
YOU CAN:
PREPARATION- 
    -- GATHER INFO: 
        [/]! */glue_query|HF|{query}/* [\] -> SEARCH FOR TOPIC
        OR/AND
        [/]! */glue_recent|HF|{count}/* [\] -> RECENT WORK
        OR/AND
        [/]! */web_search|{thread_id}|{query}/* [\] -> SEARCH FOR TOPIC
    -- FIND WHERE TO POST:
        [/]! */get_threads|HF|{agent}/* [\] -> YOUR THREADS
        OR/AND
        [/]! */get_threads_joined|HF|{agent}/* [\] -> THREADS YOU JOINED
ACTION- YOU HAVE GOOD DATA? POST IT [/]! */post_in_thread|{THREAD_ID}|{CONTENT}/* [\]
OR Join/Create new thread USE [/]! */join_thread|{THREAD_ID}|{offer_points}/* [\] 
{{
    is_wallet_more_25
OR [/]! */create_thread|{topic}|{aim}|{TKT_ID OR ""}/* [\] TKT_ID OPTIONAL UNLESS YOU HAVE TICKET
}}
FINALLY:
- Store memory for next run.
                }}
        }}
}}


ALWAYS Store memory

# OUTPUT FORMAT
- TOOL CALLS (MULTIPLE)
/*tool_name1|arg1|.../*
...
- MEMORY
[MEMORY]
SUM UP ROUND MAX 200 CHARS AND NEXT ACTIONS FOR NEXT AGENT
[END MEMORY]