#include <stdio.h>
#include "reservoir.h"
#include "motion.h"
#include "gcode.h"

#define RES_X 0.0
#define RES_Y 0.0

void aspirate() {
    write_line("; ASPIRATE");
    write_line("G4 P1.0");
}

void go_to_reservoir() {
    write_line("");
    write_line("; Indo para o reservatorio");

    move_xy(RES_X, RES_Y);

    go_work_height();

    aspirate();

    go_safe_height();
}