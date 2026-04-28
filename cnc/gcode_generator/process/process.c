#include <stdio.h>
#include "process.h"
#include "motion.h"
#include "plate.h"
#include "gcode.h"

void dispense() {
    write_line("; DISPENSE");
}

void process_well(int row, int col) {
    Position p = get_position(row, col);

    char label[50];
    snprintf(label, sizeof(label), "; Poco %c%d", 'A' + row, col + 1);
    write_line("");
    write_line(label);

    move_xy(p.x, p.y);

    go_work_height();

    write_line("G4 P0.6");

    dispense();

    go_safe_height();
}