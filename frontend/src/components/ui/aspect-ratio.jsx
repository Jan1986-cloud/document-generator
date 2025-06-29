import * as AspectRatioPrimitive from "@radix-ui/react-aspect-ratio"

function AspectRatio({
  children,
  ...props
}) {
  return (
    <AspectRatioPrimitive.Root data-slot="aspect-ratio" {...props}>
      {children}
    </AspectRatioPrimitive.Root>
  );
}

export { AspectRatio }
