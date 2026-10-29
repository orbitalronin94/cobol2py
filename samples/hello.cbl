       IDENTIFICATION DIVISION.
       PROGRAM-ID. REALTEST.
       AUTHOR. RONIN.
       DATE-WRITTEN. 2026.

       DATA DIVISION.
       WORKING-STORAGE SECTION.

       01 WS-REGISTRO.
          05 WS-TIPO          PIC X.
          05 WS-DATOS         PIC X(10).

       01 WS-REDEF.
          05 WS-CODIGO        PIC 9(3).
          05 WS-DESCRIPCION   PIC X(8).

       01 WS-TABLA.
          05 WS-ITEM         PIC 9(4) OCCURS 5 TIMES.

       01 WS-CONTADOR        PIC 9(3)  VALUE 0.
       01 WS-STATUS          PIC X     VALUE "A".
       01 WS-TOTAL           PIC 9(6)  VALUE 0.
       01 WS-PRECIO          PIC 9(5)V99 VALUE 0.
       01 WS-NOMBRE          PIC X(30) VALUE "CLIENTE".

       PROCEDURE DIVISION.
       INICIO.
           MOVE "A" TO WS-TIPO.
           MOVE 123 TO WS-CODIGO.
           MOVE 10 TO WS-ITEM(1).
           MOVE 20 TO WS-ITEM(2).
           MOVE 30 TO WS-ITEM(3).
           DISPLAY "INICIO DEL PROGRAMA".
           PERFORM PROCESAR.
           PERFORM VERIFICAR.
           STOP RUN.

       PROCESAR.
           DISPLAY "PROCESANDO...".
           PERFORM CALCULAR 3 TIMES.
           IF WS-CODIGO > 100 THEN
               DISPLAY "CODIGO ALTO"
               MOVE 0 TO WS-CODIGO
           ELSE
               DISPLAY "CODIGO BAJO"
               ADD 1 TO WS-CONTADOR
           END-IF.
           PERFORM MOSTRAR-TOTAL.

       CALCULAR.
           ADD 10 TO WS-TOTAL.
           DISPLAY "ACUMULADO: " WS-TOTAL.

       MOSTRAR-TOTAL.
           DISPLAY "TOTAL FINAL: " WS-TOTAL.

       VERIFICAR.
           IF WS-STATUS = "A" THEN
               DISPLAY "STATUS ACTIVO"
           ELSE
               IF WS-STATUS = "B" THEN
                   DISPLAY "STATUS BLOQUEADO"
               ELSE
                   DISPLAY "STATUS DESCONOCIDO"
               END-IF
           END-IF.
           IF WS-CONTADOR >= 1 THEN
               DISPLAY "SE HA PROCESADO AL MENOS UNA VEZ"
           END-IF.
           STOP RUN.
