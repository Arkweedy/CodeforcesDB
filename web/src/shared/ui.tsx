import * as Checkbox from "@radix-ui/react-checkbox";
import * as Dialog from "@radix-ui/react-dialog";
import * as Select from "@radix-ui/react-select";
import * as Tooltip from "@radix-ui/react-tooltip";
import { Check, ChevronDown, X } from "lucide-react";
import type { ReactNode } from "react";

export function IconButton({
  label,
  children,
  onClick,
  disabled = false,
  className = ""
}: {
  label: string;
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <button
          type="button"
          aria-label={label}
          className={`icon-button ${className}`}
          onClick={onClick}
          disabled={disabled}
        >
          {children}
        </button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content className="tooltip" sideOffset={6}>{label}</Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

export function CheckControl({ checked, onChange, label }: { checked: boolean; onChange: () => void; label: ReactNode }) {
  return (
    <label className="check-control">
      <Checkbox.Root className="checkbox" checked={checked} onCheckedChange={onChange}>
        <Checkbox.Indicator><Check size={13} /></Checkbox.Indicator>
      </Checkbox.Root>
      <span>{label}</span>
    </label>
  );
}

export function SelectControl<T extends string>({
  value,
  onChange,
  options,
  label
}: {
  value: T;
  onChange: (value: T) => void;
  options: Array<{ value: T; label: string }>;
  label: string;
}) {
  return (
    <Select.Root value={value} onValueChange={(next) => onChange(next as T)}>
      <Select.Trigger className="select-trigger" aria-label={label}>
        <Select.Value />
        <Select.Icon><ChevronDown size={14} /></Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="select-content" position="popper" sideOffset={5}>
          <Select.Viewport>
            {options.map((option) => (
              <Select.Item className="select-item" key={option.value} value={option.value}>
                <Select.ItemText>{option.label}</Select.ItemText>
                <Select.ItemIndicator><Check size={13} /></Select.ItemIndicator>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}

export function Modal({
  open,
  onOpenChange,
  title,
  description,
  children,
  className = ""
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className={`dialog-content ${className}`}>
          <header className="dialog-header">
            <div>
              <Dialog.Title>{title}</Dialog.Title>
              <Dialog.Description>{description}</Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button className="icon-button" aria-label="Close"><X size={18} /></button>
            </Dialog.Close>
          </header>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
