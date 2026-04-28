#ifndef PIPETTE_H
#define PIPETTE_H

typedef enum {
    PIPETTE_OK,
    PIPETTE_BUSY,
    PIPETTE_ERROR
} PipetteStatus;

void pipette_init();
void pipette_aspirate();
void pipette_dispense();
PipetteStatus pipette_get_status();

#endif