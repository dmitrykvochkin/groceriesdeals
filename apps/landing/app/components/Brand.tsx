import Link from "next/link";
import { PRODUCT_NAME, PRODUCT_NAME_ROOT, PRODUCT_NAME_SUFFIX } from "../constants";
import { BrandMark } from "./BrandMark";

export function Brand({ href = "/" }: { href?: string }) {
  const content = (
    <>
      <BrandMark />
      <span>
        {PRODUCT_NAME_ROOT}
        <span>{PRODUCT_NAME_SUFFIX}</span>
      </span>
    </>
  );

  if (href.startsWith("#")) {
    return (
      <a className="brand" href={href} aria-label={`${PRODUCT_NAME} home`}>
        {content}
      </a>
    );
  }

  return (
    <Link className="brand" href={href} aria-label={`${PRODUCT_NAME} home`}>
      {content}
    </Link>
  );
}
