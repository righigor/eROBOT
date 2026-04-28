# ===== CONFIG =====
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -I. -Igcode -Imotion -Iplate -Iprocess

TARGET = cnc-test

SRC = main.c \
      gcode/gcode.c \
      motion/motion.c \
      plate/plate.c \
      process/process.c

OBJ = $(SRC:.c=.o)

# ===== BUILD =====
all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJ)

# ===== REGRA GENÉRICA =====
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# ===== LIMPEZA =====
clean:
	rm -f $(OBJ) $(TARGET)

# ===== EXECUTAR =====
run: $(TARGET)
	./$(TARGET)

# ===== REBUILD =====
re: clean all