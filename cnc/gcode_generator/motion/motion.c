#include <stdio.h>
#include "motion.h"
#include "gcode.h"
#include "config.h"

static int is_at_safe_height = 1;

void go_safe_height() {
    if (!is_at_safe_height) {
        char buffer[50];
        snprintf(buffer, sizeof(buffer), "G1 Z%.2f F%d", Z_SAFE, FEED_Z);
        write_line(buffer);
        is_at_safe_height = 1;
    }
}

void go_work_height() {
    char buffer[50];
    snprintf(buffer, sizeof(buffer), "G1 Z%.2f F%d", Z_WORK, FEED_Z);
    write_line(buffer);
    is_at_safe_height = 0;
}

void move_xy(float x, float y) {
    go_safe_height();

    char buffer[100];
    snprintf(buffer, sizeof(buffer), "G1 X%.2f Y%.2f F%d", x, y, FEED_XY);
    write_line(buffer);
}