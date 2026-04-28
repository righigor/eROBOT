#include <stdio.h>
#include "gcode.h"

static FILE *gcode;

void write_line(const char *line) {
    fprintf(gcode, "%s\n", line);
}

void init_gcode() {
    gcode = fopen("output.gcode", "w");

    if (!gcode) {
        printf("Erro ao criar arquivo\n");
        return;
    }

    write_line("G21");
    write_line("G90");
    write_line("G17");
    write_line("G94");

    write_line("G0 Z5");
    write_line("G0 X0 Y0");
}

void finish_gcode() {
    write_line("");
    write_line("G0 Z5");
    write_line("G0 X0 Y0");
    write_line("M2");

    fclose(gcode);
}