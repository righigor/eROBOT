#include <stdio.h>
#include <unistd.h>
#include "pipette.h"

static PipetteStatus status = PIPETTE_OK;

void pipette_init() {
    printf("[PIPETA] Inicializada\n");
}

void pipette_aspirate() {
    printf("[PIPETA] Aspirando...\n");
    status = PIPETTE_BUSY;

    sleep(1);

    status = PIPETTE_OK;
    printf("[PIPETA] Aspiracao concluida\n");
}

void pipette_dispense() {
    printf("[PIPETA] Dispensando...\n");
    status = PIPETTE_BUSY;

    sleep(1);

    status = PIPETTE_OK;
    printf("[PIPETA] Dispensa concluida\n");
}

PipetteStatus pipette_get_status() {
    return status;
}