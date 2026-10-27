       IDENTIFICATION DIVISION.
       PROGRAM-ID. LABERINTO-COBOL.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-STEP PIC 9 VALUE 1.
       01 WS-ACC PIC 9(6) VALUE 100.
       01 WS-RAW-INPUT PIC X(10).
       01 WS-VIEW REDEFINES WS-RAW-INPUT.
          05 WS-A PIC 9(5).
          05 WS-B PIC 9(5).
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY "INICIO DEL LABERINTO COBOL".
           ALTER PUNTO-X TO PROCEED TO PUNTO-Y.
           GO TO PUNTO-A.
       PUNTO-A.
           ADD 10 TO WS-ACC.
           GO TO PUNTO-X.
       PUNTO-X.
           GO TO PUNTO-B.
       PUNTO-Y.
           COMPUTE WS-ACC = WS-ACC * 2.
           GO TO PUNTO-B.
       PUNTO-Z.
           SUBTRACT 5 FROM WS-ACC.
           GO TO PUNTO-B.
       PUNTO-B.
           GO TO P-VAL-1 P-VAL-2 P-VAL-3 DEPENDING ON WS-STEP.
           GO TO FINAL-ROUTINE.
       P-VAL-1.
           MOVE 2 TO WS-STEP.
           ALTER PUNTO-X TO PROCEED TO PUNTO-Z.
           GO TO PUNTO-A.
       P-VAL-2.
           MOVE "9999911111" TO WS-RAW-INPUT.
           COMPUTE WS-ACC = WS-A + WS-B.
           MOVE 3 TO WS-STEP.
           GO TO MAIN-LOGIC.
       P-VAL-3.
           MOVE 99 TO WS-STEP.
           GO TO FINAL-ROUTINE.
       FINAL-ROUTINE.
           DISPLAY "RESULTADO FINAL ACUMULADOR: " WS-ACC.
           STOP RUN.
