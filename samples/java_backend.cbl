       IDENTIFICATION DIVISION.
       PROGRAM-ID. JAVATEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-NAME PIC X(5) VALUE "AL".
       01 WS-COUNT PIC 9(3) VALUE 0.
       PROCEDURE DIVISION.
       MAIN.
           MOVE "BOB" TO WS-NAME.
           ADD 2 TO WS-COUNT.
           DISPLAY WS-NAME.
           DISPLAY WS-COUNT.
           IF WS-COUNT = 2
               DISPLAY "MATCH"
           ELSE
               DISPLAY "MISS"
           END-IF.
           EVALUATE WS-COUNT
               WHEN 2
                   DISPLAY "TWO"
               WHEN OTHER
                   DISPLAY "OTHER"
           END-EVALUATE.
           STOP RUN.
