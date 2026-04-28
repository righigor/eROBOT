#include "plate.h"
#include "config.h"

Position get_position(int row, int col) {
    Position p;

    p.x = X0 + col * PITCH;
    p.y = Y0 + row * PITCH;

    return p;
}