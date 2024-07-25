p_inds = np.empty((0, 2))
    inflections = np.where(np.diff(delta_depth) != 0)[0]
    if len(inflections) > 0:
        p_inds = np.append(p_inds, [[0, inflections[0]]], axis=0)
    for p in range(len(inflections) - 1):
        p_inds = np.append(p_inds, [[inflections[p], inflections[p + 1]]], axis=0)
    if len(inflections) > 0:
        p_inds = np.append(p_inds, [[inflections[-1], len(ts) - 1]], axis=0)
    # profile_timestamps = np.empty((0,2))
    ts_window = tsint * 2
