       IDENTIFICATION DIVISION.
       PROGRAM-ID. B041.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC 9 VALUE 2.
       01 WS-B PIC 9 VALUE 3.
       PROCEDURE DIVISION.
       MAIN-PARA.
           IF WS-A = 2 AND WS-B = 3
               DISPLAY "BOTH"
           ELSE
               DISPLAY "OTHER"
           END-IF.
           STOP RUN.
