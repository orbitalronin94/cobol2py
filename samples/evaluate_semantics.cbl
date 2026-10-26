       IDENTIFICATION DIVISION.
       PROGRAM-ID. EVALUATE-SEMANTICS.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-CODE PIC 9 VALUE 2.
       PROCEDURE DIVISION.
       MAIN.
           EVALUATE WS-CODE
               WHEN 1
                   DISPLAY "ONE"
               WHEN 2
                   DISPLAY "TWO"
               WHEN OTHER
                   DISPLAY "OTHER"
           END-EVALUATE.
           EVALUATE TRUE
               WHEN WS-CODE > 1
                   DISPLAY "TRUE-BRANCH"
               WHEN OTHER
                   DISPLAY "FALSE-BRANCH"
           END-EVALUATE.
           STOP RUN.
