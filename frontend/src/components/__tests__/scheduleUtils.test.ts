import { describe, it, expect } from 'vitest'
import { toMinutes, assignLayers } from '../SchedulePanel'

const makeEvent = (id: string, start: string, end: string) => ({
  event_id: id,
  date: '2026-07-18',
  start_time: start,
  end_time: end,
  event: `Event ${id}`,
  protected: false,
})

describe('toMinutes', () => {
  it('converts 00:00 to 0', () => {
    expect(toMinutes('00:00')).toBe(0)
  })

  it('converts 09:30 to 570', () => {
    expect(toMinutes('09:30')).toBe(570)
  })

  it('converts 23:59 to 1439', () => {
    expect(toMinutes('23:59')).toBe(1439)
  })

  it('handles HH:MM:SS strings by slicing to HH:MM', () => {
    expect(toMinutes('14:00:00')).toBe(840)
  })
})

describe('assignLayers', () => {
  it('places a single event on layer 0', () => {
    const [e] = assignLayers([makeEvent('a', '09:00', '10:00')])
    expect(e.layer).toBe(0)
  })

  it('places non-overlapping events on the same layer', () => {
    const [e1, e2] = assignLayers([
      makeEvent('a', '09:00', '10:00'),
      makeEvent('b', '11:00', '12:00'),
    ])
    expect(e1.layer).toBe(0)
    expect(e2.layer).toBe(0)
  })

  it('pushes overlapping events to separate layers', () => {
    const events = assignLayers([
      makeEvent('a', '09:00', '11:00'),
      makeEvent('b', '09:00', '11:00'),
    ])
    const layers = events.map((e) => e.layer)
    expect(layers).toContain(0)
    expect(layers).toContain(1)
  })

  it('correctly computes startPct for a noon event', () => {
    const [e] = assignLayers([makeEvent('a', '12:00', '13:00')])
    expect(e.startPct).toBeCloseTo(50, 1)
  })

  it('sets minimum widthPct of 0.5 for zero-width edge case', () => {
    const [e] = assignLayers([makeEvent('a', '00:00', '00:01')])
    expect(e.widthPct).toBeGreaterThanOrEqual(0.5)
  })
})
