#ifndef PLATE_H
#define PLATE_H

typedef struct {
    float x;
    float y;
} Position;

Position get_position(int row, int col);

#endif