       IDENTIFICATION DIVISION.
       PROGRAM-ID. B021.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC 9 VALUE 1.
       01 WS-B PIC 9 VALUE 2.
       PROCEDURE DIVISION.
       MAIN-PARA.
       IF WS-A = 1
          IF WS-B = 2
             DISPLAY "BOTH"
          ELSE
             DISPLAY "INNER-NO"
          END-IF
       ELSE
          DISPLAY "OUTER-NO"
       END-IF.
       STOP RUN.
