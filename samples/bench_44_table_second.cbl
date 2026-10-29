       IDENTIFICATION DIVISION.
       PROGRAM-ID. B044.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-IDX PIC 9 VALUE 2.
       01 WS-TABLE.
          05 WS-ITEM PIC X(4) OCCURS 3 TIMES.
       PROCEDURE DIVISION.
       MAIN-PARA.
           MOVE "RED" TO WS-ITEM(1).
           MOVE "BLU" TO WS-ITEM(2).
           IF WS-ITEM(2) = "BLU"
               DISPLAY "SECOND-OK"
           ELSE
               DISPLAY "SECOND-NO"
           END-IF.
           STOP RUN.
