package health

import "sync/atomic"

type State struct {
	ready atomic.Bool
}

func NewState() *State {
	return &State{}
}

func (state *State) MarkReady() {
	state.ready.Store(true)
}

func (state *State) MarkNotReady() {
	state.ready.Store(false)
}

func (state *State) IsReady() bool {
	return state.ready.Load()
}
