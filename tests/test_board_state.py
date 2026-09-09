import numpy as np

from chalkline.board_state import BoardState, ChangeKind


def settle(state, frame, occluded, count=6):
    commits = []
    for _ in range(count):
        result = state.observe(frame, occluded)
        if result: commits.append(result)
    return commits


def test_presenter_never_overwrites_verified_writing():
    state = BoardState((32, 32), mask_hold_frames=1)
    board = np.full((32, 32, 3), 30, np.uint8)
    state.observe(board, np.zeros((32, 32), bool))
    board[10:13, 5:25] = 230
    assert settle(state, board, np.zeros((32, 32), bool))
    preserved = state.image.copy()
    presenter = board.copy(); presenter[4:28, 8:24] = (40, 80, 160)
    mask = np.zeros((32, 32), bool); mask[4:28, 8:24] = True
    settle(state, presenter, mask)
    assert np.array_equal(state.image, preserved)
    assert state.stale[12, 12]


def test_erasure_requires_more_clear_observations():
    state = BoardState((32, 32), update_observations=2, erase_observations=4, mask_hold_frames=0)
    clean = np.full((32, 32, 3), 25, np.uint8)
    state.observe(clean, np.zeros((32, 32), bool))
    written = clean.copy(); written[10:14, 4:28] = 240
    commits = settle(state, written, np.zeros((32, 32), bool), 3)
    assert commits[-1].kind == ChangeKind.UPDATE
    erased = clean.copy()
    assert not settle(state, erased, np.zeros((32, 32), bool), 3)
    commits = settle(state, erased, np.zeros((32, 32), bool), 2)
    assert commits[-1].kind == ChangeKind.ERASURE


def test_lighting_jump_freezes_commits():
    state = BoardState((20, 20), update_observations=1, mask_hold_frames=0)
    dark = np.full((20, 20, 3), 20, np.uint8)
    state.observe(dark, np.zeros((20, 20), bool))
    assert state.observe(np.full_like(dark, 90), np.zeros((20, 20), bool)) is None
    assert state.stale.all()
