def check_winner(board):
    # Проверяем горизонтали и вертикали
    for i in range(3):
        if board[i * 3] == board[i * 3 + 1] == board[i * 3 + 2] != 'empty':
            return True, board[i * 3].callback_data  # Возвращаем True и символ победителя
        if board[i] == board[i + 3] == board[i + 6] != 'empty':
            return True, board[i].callback_data  # Возвращаем True и символ победителя

    # Проверяем диагонали
    if board[0] == board[4] == board[8] != 'empty':
        return True, board[0].callback_data  # Возвращаем True и символ победителя
    if board[2] == board[4] == board[6] != 'empty':
        return True, board[2].callback_data  # Возвращаем True и символ победителя

    # Если ни одна из выигрышных комбинаций не найдена
    return False, None
