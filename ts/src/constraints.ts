/** Constraint taxonomy types (CDL — Constraint Detection Layer). */

import type { ParseResult } from "./parser.js"

export enum ConstraintType {
  TECHNICAL = "technical",
  FINANCIAL = "financial",
  TEMPORAL = "temporal",
  HUMAN = "human",
  SEMANTIC = "semantic",
  INTEGRATION = "integration",
  EMERGENT = "emergent",
}

export enum ConstraintCategory {
  HARD = "hard",
  SOFT = "soft",
  FALSE = "false",
}

export enum ConstraintLevel {
  FEDERATION = "federation",
  GUILD = "guild",
  AGENT = "agent",
  ENTRY_POINT = "entry_point",
}

export interface Constraint {
  rawText: string
  constraintType: ConstraintType
  constraintCategory: ConstraintCategory
  quantifiable: boolean
  relaxable: boolean
  priority: number
}

const HARD_KINDS = new Set(["requirement", "exact", "dependency", "negation"])
const FALSE_KINDS = new Set(["assumption"])

function categorizeByKind(kind: string): ConstraintCategory {
  if (HARD_KINDS.has(kind)) return ConstraintCategory.HARD
  if (FALSE_KINDS.has(kind)) return ConstraintCategory.FALSE
  return ConstraintCategory.SOFT
}

const KIND_TYPE_MAP: Record<string, ConstraintType> = {
  exact: ConstraintType.SEMANTIC,
  requirement: ConstraintType.TECHNICAL,
  negation: ConstraintType.SEMANTIC,
  dependency: ConstraintType.INTEGRATION,
  assumption: ConstraintType.EMERGENT,
  conditional: ConstraintType.SEMANTIC,
}

function typeForKind(kind: string): ConstraintType {
  return KIND_TYPE_MAP[kind] ?? ConstraintType.TECHNICAL
}

export function upgradeConstraints(result: ParseResult): Constraint[] {
  const typed: Constraint[] = []
  for (const kind of result.constraints) {
    const ct = typeForKind(kind)
    const cat = categorizeByKind(kind)
    const quant = kind === "exact"
    const relax = kind === "conditional"
    typed.push({
      rawText: kind,
      constraintType: ct,
      constraintCategory: cat,
      quantifiable: quant,
      relaxable: relax,
      priority: 5,
    })
  }
  return typed
}

export interface ConstraintAnalysis {
  typed: Constraint[]
  hardCount: number
  softCount: number
  falseCount: number
  missingTypes: ConstraintType[]
}

export function constraintAnalysisFromParse(result: ParseResult): ConstraintAnalysis {
  const typed = upgradeConstraints(result)
  const hard = typed.filter((c) => c.constraintCategory === ConstraintCategory.HARD).length
  const soft = typed.filter((c) => c.constraintCategory === ConstraintCategory.SOFT).length
  const falseC = typed.filter((c) => c.constraintCategory === ConstraintCategory.FALSE).length
  const foundTypes = new Set(typed.map((c) => c.constraintType))
  const missing = Object.values(ConstraintType).filter((t) => !foundTypes.has(t))
  return {
    typed,
    hardCount: hard,
    softCount: soft,
    falseCount: falseC,
    missingTypes: missing,
  }
}
