#include "gcode.h"
#include "process.h"

int main() {
    init_gcode();

    for (int row = 0; row < 4; row++) {
        if (row % 2 == 0) {
            for (int col = 0; col < 6; col++) {
                process_well(row, col);
            }
        } else {
            for (int col = 5; col >= 0; col--) {
                process_well(row, col);
            }
        }
    }

    finish_gcode();

    return 0;
}