type ClassValue = string | number | boolean | undefined | null | ClassValue[]

function clsx(...inputs: ClassValue[]): string {
  return inputs.filter(Boolean).join(' ')
}

export function cn(...inputs: ClassValue[]) {
  return clsx(...inputs)
}
